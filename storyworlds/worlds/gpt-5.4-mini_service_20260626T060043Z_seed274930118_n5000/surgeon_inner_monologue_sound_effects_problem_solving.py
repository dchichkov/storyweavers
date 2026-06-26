#!/usr/bin/env python3
"""
A standalone storyworld: an animal surgeon faces a small problem, thinks it
through in an inner monologue, and solves it with careful sound-filled actions.

The domain is intentionally small and classical:
- a surgeon character who must prepare for a tiny clinic problem
- a worried patient animal
- a few tools and a limited set of plausible fixes
- narrated inner monologue, sound effects, and concrete problem solving

The story is generated from a simulated world model, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"surgeon", "doctor", "boy", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"nurse", "girl", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little animal clinic"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    use: str
    sound: str
    fixs: set[str]


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    symptom: str
    fix_needed: str
    sound: str
    risk: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        w.facts = dict(self.facts)
        return w

    def log(self, line: str) -> None:
        self.trace_log.append(line)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "clinic": Setting(place="the little animal clinic", affords={"checkup", "stitch", "clean"}),
    "barn": Setting(place="the barn clinic", affords={"checkup", "stitch"}),
    "treehouse": Setting(place="the treehouse clinic", affords={"checkup", "clean"}),
}

PROBLEMS = {
    "tiny-cut": Problem(
        id="tiny-cut",
        label="tiny cut",
        phrase="a tiny cut on the paw",
        symptom="the paw kept oozing a little red drop",
        fix_needed="stitch",
        sound="drip-drip",
        risk="the cut could open wider",
        tags={"paw", "blood", "stitch"},
    ),
    "splinter": Problem(
        id="splinter",
        label="splinter",
        phrase="a splinter in the toe",
        symptom="the toe kept twitching and flinching",
        fix_needed="clean",
        sound="tap-tap",
        risk="the splinter could poke deeper",
        tags={"toe", "wood", "clean"},
    ),
    "muddy-ear": Problem(
        id="muddy-ear",
        label="muddy ear",
        phrase="a muddy ear",
        symptom="the ear was floppy and dirty",
        fix_needed="clean",
        sound="swish-swish",
        risk="the dirt could irritate the ear",
        tags={"ear", "mud", "clean"},
    ),
}

TOOLS = [
    Tool(
        id="lamp",
        label="a bright lamp",
        kind="light",
        use="see the tiny problem clearly",
        sound="click",
        fixs=set(),
    ),
    Tool(
        id="soap-bowl",
        label="a warm bowl of soap",
        kind="cleaning",
        use="wash away dirt",
        sound="glug-glug",
        fixs={"clean"},
    ),
    Tool(
        id="needle",
        label="a tiny curved needle",
        kind="stitching",
        use="stitch a cut neatly",
        sound="tink-tink",
        fixs={"stitch"},
    ),
    Tool(
        id="tweezers",
        label="a pair of tweezers",
        kind="pinch",
        use="pull out a splinter",
        sound="snip",
        fixs={"clean"},
    ),
    Tool(
        id="bandage",
        label="a soft bandage",
        kind="covering",
        use="protect a fixed spot",
        sound="wrap-wrap",
        fixs={"stitch", "clean"},
    ),
]

ANIMAL_NAMES = ["Milo", "Pip", "Poppy", "Maya", "Toby", "Bibi", "Luna", "Otto"]
SURGEON_NAMES = ["Dr. Reed", "Dr. Finch", "Dr. Willow", "Dr. Moss"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    surgeon_name: str
    patient_name: str
    patient_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return problem.fix_needed in tool.fixs


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            if prob.fix_needed in {"stitch", "clean"} and setting.affords:
                combos.append((setting_id, prob_id))
    return combos


def choose_best_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem_needs_tool(problem, tool):
            return tool
    return None


def sound_for_tool(tool: Tool) -> str:
    return tool.sound


def sound_for_problem(problem: Problem) -> str:
    return problem.sound


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def introduce(world: World, surgeon: Entity, patient: Entity, problem: Problem) -> None:
    world.say(
        f"{surgeon.id} was the kind of surgeon who loved helping small animals at {world.setting.place}."
    )
    world.say(
        f"One day {patient.id} arrived with {problem.phrase}."
    )
    world.say(
        f"{patient.id} looked small and worried, and {problem.symptom}."
    )


def think(world: World, surgeon: Entity, problem: Problem) -> None:
    world.say(
        f"{surgeon.id} took one slow breath. \""
        f"I need to stay calm,\" {surgeon.pronoun('subject')} thought."
    )
    world.say(
        f"\"If I choose the wrong tool, {problem.risk}.\""
    )
    world.facts["inner_monologue"] = True


def examine(world: World, surgeon: Entity, problem: Problem) -> None:
    world.say(
        f"{surgeon.id} leaned closer. Click. The lamp blinked on, and the tiny problem shone in the light."
    )
    world.say(
        f"\"First I look, then I fix,\" {surgeon.pronoun('subject')} thought."
    )


def solve(world: World, surgeon: Entity, patient: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"{surgeon.id} chose {tool.label} because it could {tool.use}."
    )
    world.say(
        f"{sound_for_tool(tool).capitalize()}! {surgeon.id} worked carefully."
    )
    if problem.fix_needed == "clean":
        world.say(
            f"Swish-swish went the warm soap water, and the muddy bit came off at last."
        )
    elif problem.fix_needed == "stitch":
        world.say(
            f"Tink-tink went the tiny needle, neat and gentle, until the cut was closed."
        )
    world.say(
        f"Then {patient.id} gave a little sigh, because {problem.sound} was gone."
    )
    patient.memes["relief"] = patient.memes.get("relief", 0.0) + 1.0
    surgeon.memes["pride"] = surgeon.memes.get("pride", 0.0) + 1.0


def finish(world: World, surgeon: Entity, patient: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"{patient.id} wagged {patient.it()} tail or twitched {patient.it()} ears in happy relief."
    )
    world.say(
        f"{surgeon.id} smiled. The little animal was safe again, and the clinic felt quiet and warm."
    )
    world.facts["resolved"] = True
    world.facts["tool"] = tool


def tell(setting: Setting, problem: Problem, surgeon_name: str, patient_name: str, patient_type: str) -> World:
    world = World(setting)
    surgeon = world.add(Entity(id=surgeon_name, kind="character", type="surgeon", label="surgeon"))
    patient = world.add(Entity(id=patient_name, kind="character", type=patient_type, label=patient_type))
    world.facts["surgeon"] = surgeon
    world.facts["patient"] = patient
    world.facts["problem"] = problem

    introduce(world, surgeon, patient, problem)
    world.para()
    think(world, surgeon, problem)
    examine(world, surgeon, problem)
    tool = choose_best_tool(problem)
    if tool is None:
        raise StoryError("No reasonable tool exists for this problem.")
    solve(world, surgeon, patient, problem, tool)
    finish(world, surgeon, patient, problem, tool)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem: Problem = f["problem"]
    patient: Entity = f["patient"]
    surgeon: Entity = f["surgeon"]
    return [
        f"Write a gentle animal story about {surgeon.id} helping {patient.id} with {problem.phrase}.",
        f"Tell a short story where a surgeon thinks carefully, makes small sound effects, and solves a clinic problem.",
        f"Write an animal story that includes an inner monologue and ends with a happy fix for {problem.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem: Problem = f["problem"]
    patient: Entity = f["patient"]
    surgeon: Entity = f["surgeon"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who helped {patient.id} at the clinic?",
            answer=f"{surgeon.id} helped {patient.id} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was wrong with {patient.id}?",
            answer=f"{patient.id} had {problem.phrase}.",
        ),
        QAItem(
            question=f"What tool did {surgeon.id} choose to fix it?",
            answer=f"{surgeon.id} chose {tool.label} because it could {tool.use}.",
        ),
        QAItem(
            question="What was the surgeon thinking about before acting?",
            answer=(
                f"{surgeon.id} was thinking about choosing the right tool so the problem would not get worse."
            ),
        ),
        QAItem(
            question="What happened at the end?",
            answer=(
                f"The problem was fixed, {patient.id} felt better, and the clinic became calm again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a surgeon do?",
            answer="A surgeon helps heal bodies by carefully fixing injuries and problems, often with special tools.",
        ),
        QAItem(
            question="Why do doctors wash their hands?",
            answer="Doctors wash their hands so they do not spread germs while helping a patient.",
        ),
        QAItem(
            question="Why are small tools useful in a clinic?",
            answer="Small tools help a surgeon work carefully on little problems without hurting the patient.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.extend(world.trace_log)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/2.

valid_story(S, P) :- setting(S), problem(P), solvable(S, P).
solvable(S, P) :- affords(S, clean), fix_needed(P, clean).
solvable(S, P) :- affords(S, stitch), fix_needed(P, stitch).
"""


def asp_facts() -> str:
    import asp
    parts: list[str] = []
    for sid, setting in SETTINGS.items():
        parts.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            parts.append(asp.fact("affords", sid, a))
    for pid, prob in PROBLEMS.items():
        parts.append(asp.fact("problem", pid))
        parts.append(asp.fact("fix_needed", pid, prob.fix_needed))
    return "\n".join(parts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity holds for {len(py)} combos.")
        return 0
    print("MISMATCH between Python and ASP.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params, resolution, generation
# ---------------------------------------------------------------------------

@dataclass
class Resolved:
    setting: str
    problem: str
    surgeon_name: str
    patient_name: str
    patient_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story surgeon world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--surgeon-name")
    ap.add_argument("--patient-name")
    ap.add_argument("--patient-type", choices=["mouse", "rabbit", "fox", "cat", "dog", "bird"])
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
    combos = valid_combos()
    if args.setting and args.problem:
        if (args.setting, args.problem) not in combos:
            raise StoryError("That setting/problem pair is not reasonable for this small clinic story.")
    if args.setting:
        settings = [args.setting]
    else:
        settings = sorted(SETTINGS)
    if args.problem:
        problems = [args.problem]
    else:
        problems = sorted(PROBLEMS)

    valid = [(s, p) for s, p in combos if s in settings and p in problems]
    if not valid:
        raise StoryError("No valid combination matches the given options.")

    setting, problem = rng.choice(valid)
    surgeon_name = args.surgeon_name or rng.choice(SURGEON_NAMES)
    patient_name = args.patient_name or rng.choice(ANIMAL_NAMES)
    patient_type = args.patient_type or rng.choice(["mouse", "rabbit", "fox", "cat", "dog", "bird"])
    return StoryParams(
        setting=setting,
        problem=problem,
        surgeon_name=surgeon_name,
        patient_name=patient_name,
        patient_type=patient_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        params.surgeon_name,
        params.patient_name,
        params.patient_type,
    )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="clinic", problem="tiny-cut", surgeon_name="Dr. Finch", patient_name="Milo", patient_type="cat"),
    StoryParams(setting="barn", problem="splinter", surgeon_name="Dr. Moss", patient_name="Pip", patient_type="rabbit"),
    StoryParams(setting="treehouse", problem="muddy-ear", surgeon_name="Dr. Willow", patient_name="Poppy", patient_type="fox"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, p in combos:
            print(f"{s} {p}")
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.surgeon_name}: {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
