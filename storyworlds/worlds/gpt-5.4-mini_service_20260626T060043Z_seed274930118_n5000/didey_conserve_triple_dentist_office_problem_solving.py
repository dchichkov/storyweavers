#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/didey_conserve_triple_dentist_office_problem_solving.py
=================================================================================================

A small, standalone storyworld in a dentist office.
The seed tale is built around a brave child detective, a simple problem-solving
turn, and a gentle resolution.

Core premise:
- Didey notices a mystery in a dentist office.
- Something important is missing or wrong.
- Didey uses bravery and problem solving to help fix it.
- The ending proves the change with a concrete, state-driven image.

This world is intentionally small and constraint-driven, with an ASP twin for
reasonableness parity and verification.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dentist office"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    keyword: str
    symptom: str
    cause: str
    clue: str
    severity: str
    fix_hint: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fits: set[str]


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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_missing_tool(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Didey")
    problem = world.facts.get("problem")
    tool = world.facts.get("tool")
    if not problem or not tool:
        return out
    if detective.memes.get("curious", 0.0) < THRESHOLD:
        return out
    if detective.memes.get("brave", 0.0) < THRESHOLD:
        return out
    sig = ("missing_tool", problem.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["resolve"] = detective.memes.get("resolve", 0.0) + 1
    out.append("Didey noticed the clue and stayed calm.")
    return out


def _r_fix_problem(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts.get("problem")
    tool = world.facts.get("tool")
    if not problem or not tool:
        return out
    detective = world.get("Didey")
    if detective.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("fixed", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["fixed"] = True
    detective.memes["pride"] = detective.memes.get("pride", 0.0) + 1
    out.append("The office felt safer after the problem was solved.")
    return out


CAUSAL_RULES = [_r_missing_tool, _r_fix_problem]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def detect_problem(world: World, detective: Entity, problem: Problem) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0.0) + 1
    world.say(
        f"{detective.id} was a little detective who noticed every tiny clue at {world.setting.place}."
    )
    world.say(
        f"One day, {detective.id} saw that {problem.symptom}."
    )


def frame_setting(world: World, problem: Problem) -> None:
    world.say(
        f"The dentist office was bright and clean, but something still felt off near the chair."
    )
    world.say(
        f"A small mystery was hiding in plain sight: {problem.keyword}."
    )


def present_case(world: World, detective: Entity, parent: Entity, problem: Problem) -> None:
    detective.memes["brave"] = detective.memes.get("brave", 0.0) + 1
    world.say(
        f"{detective.id} took a brave breath and told {parent.label or parent.id} what {detective.pronoun('subject')} had found."
    )
    world.say(
        f"{detective.pronoun('possessive').capitalize()} careful eyes pointed to {problem.clue}."
    )


def hesitate(world: World, detective: Entity, problem: Problem) -> None:
    world.say(
        f"For a moment, {detective.id} felt a small wobble in {detective.pronoun('possessive')} knees."
    )
    world.say(
        f"But {detective.pronoun('subject').capitalize()} remembered that brave people solve problems one clue at a time."
    )


def solve_case(world: World, detective: Entity, parent: Entity, problem: Problem, tool: Tool) -> None:
    detective.memes["resolve"] = detective.memes.get("resolve", 0.0) + 1
    world.say(
        f"Together, they used {tool.phrase} because it fit the job."
    )
    world.say(
        f"That simple plan made the {problem.severity} trouble disappear."
    )
    propagate(world, narrate=True)


def ending_image(world: World, detective: Entity, problem: Problem, tool: Tool) -> None:
    if world.facts.get("fixed"):
        world.say(
            f"In the end, {detective.id} smiled beside the chair, and {tool.label} sat ready for the next little job."
        )
        world.say(
            f"The dentist office was quiet again, and the mystery was no longer a mystery."
        )
    else:
        world.say(
            f"The mystery still waited, but {detective.id} kept watch with brave eyes."
        )


def tell(setting: Setting, problem: Problem, tool: Tool, name: str = "Didey") -> World:
    world = World(setting)

    detective = world.add(Entity(
        id=name,
        kind="character",
        type="boy",
        traits=["curious", "brave", "careful"],
    ))
    parent = world.add(Entity(
        id="DentistHelper",
        kind="character",
        type="adult",
        label="the dentist helper",
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        type="thing",
        label=tool.label,
        phrase=tool.phrase,
        caretaker=parent.id,
        location=setting.place,
    ))

    world.facts["problem"] = problem
    world.facts["tool"] = tool_ent
    world.facts["tool_def"] = tool

    frame_setting(world, problem)
    world.para()
    detect_problem(world, detective, problem)
    present_case(world, detective, parent, problem)
    hesitate(world, detective, problem)
    world.para()
    solve_case(world, detective, parent, problem, tool)
    ending_image(world, detective, problem, tool)
    return world


SETTING = Setting(place="the dentist office", affords={"problem_solving", "bravery"})


PROBLEMS = {
    "triple": Problem(
        id="triple",
        keyword="triple",
        symptom="the appointment list had a triple mark on it",
        cause="three visits had been written in the wrong place",
        clue="the extra marks on the clipboard",
        severity="tricky",
        fix_hint="sort the list one line at a time",
    ),
    "sticker": Problem(
        id="sticker",
        keyword="sticker",
        symptom="the prize sticker box was empty",
        cause="someone had taken the last star sticker",
        clue="an open drawer under the counter",
        severity="small",
        fix_hint="find the missing sticker",
    ),
    "buzzer": Problem(
        id="buzzer",
        keyword="buzzer",
        symptom="the little waiting-room buzzer would not ring",
        cause="its battery had slipped loose",
        clue="a loose battery near the base",
        severity="nagging",
        fix_hint="press the battery back into place",
    ),
}

TOOLS = {
    "clipboard": Tool(
        id="clipboard",
        label="the clipboard",
        phrase="the clipboard with the neat list",
        helps={"triple", "sticker"},
        fits={"problem_solving"},
    ),
    "lamp": Tool(
        id="lamp",
        label="the desk lamp",
        phrase="the desk lamp for a closer look",
        helps={"buzzer"},
        fits={"problem_solving"},
    ),
    "stool": Tool(
        id="stool",
        label="the small stool",
        phrase="the small stool to reach the shelf",
        helps={"sticker"},
        fits={"problem_solving", "bravery"},
    ),
}

NAMES = ["Didey"]
TRAITS = ["curious", "brave", "careful"]


@dataclass
class StoryParams:
    problem: str
    tool: str
    name: str = "Didey"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, problem in PROBLEMS.items():
        for tid, tool in TOOLS.items():
            if pid in tool.helps and "problem_solving" in tool.fits:
                combos.append((pid, tid))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not help with {problem.keyword} in a way "
        f"that fits the dentist-office problem-solving premise.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective-style dentist office story world about bravery and problem solving."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
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
        if (args.problem, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.problem is None or c[0] == args.problem)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, tool = rng.choice(sorted(combos))
    return StoryParams(problem=problem, tool=tool, name=args.name or "Didey")


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    t = world.facts["tool_def"]
    return [
        f'Write a short detective story for children set in a dentist office about "{p.keyword}".',
        f"Tell a brave little mystery where Didey notices {p.symptom} and uses {t.label} to help.",
        f"Write a gentle problem-solving story in a dentist office that includes the word '{p.keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    t = world.facts["tool_def"]
    fixed = bool(world.facts.get("fixed"))
    return [
        QAItem(
            question=f"What mystery did Didey notice in the dentist office?",
            answer=f"Didey noticed that {p.symptom}. It was a small detective mystery in the dentist office.",
        ),
        QAItem(
            question=f"How did Didey solve the problem?",
            answer=f"Didey stayed brave, looked carefully at {p.clue}, and used {t.label} to help fix it.",
        ),
        QAItem(
            question=f"Why was Didey a brave detective?",
            answer=(
                f"Didey was brave because {world.setting.place} had a problem that needed a calm helper, "
                f"and Didey spoke up instead of backing away."
            ),
        ),
        QAItem(
            question=f"Was the problem solved by the end?",
            answer="Yes, the problem was solved and the dentist office felt calm again."
            if fixed else
            "Not yet, but Didey was still watching the clues carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dentist office?",
            answer="A dentist office is a place where people go to check and clean their teeth.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking at a problem, thinking carefully, and trying a good fix.",
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(problem).
problem(triple).
tool(clipboard).
tool(lamp).
tool(stool).

helps(clipboard,triple).
helps(clipboard,sticker).
helps(lamp,buzzer).
helps(stool,sticker).

fits(clipboard,problem).
fits(lamp,problem).
fits(stool,problem).
fits(stool,bravery).

valid(P,T) :- problem(P), tool(T), helps(T,P), fits(T,problem).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for tid, tool in TOOLS.items():
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, p))
        for f in sorted(tool.fits):
            lines.append(asp.fact("fits", tid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, PROBLEMS[params.problem], TOOLS[params.tool], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/2;"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible problem/tool combos:\n")
        for p, t in combos:
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, t in valid_combos():
            params = StoryParams(problem=p, tool=t, name="Didey")
            samples.append(generate(params))
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
